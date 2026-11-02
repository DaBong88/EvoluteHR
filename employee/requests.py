"""Manager-facing team request workspace for EvoluteHR."""

import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from horilla.decorators import hx_request_required

from employee.models import Employee, EmployeeWorkInformation, ReportingManagerChangeRequest


def _manager_for(request):
    employee = getattr(request.user, "employee_get", None)
    if request.user.is_superuser or request.user.is_staff:
        return employee
    if employee and EmployeeWorkInformation.objects.filter(
        reporting_manager_id=employee, employee_id__is_active=True
    ).exists():
        return employee
    return None


def _team_members(request, manager):
    employees = Employee.objects.filter(is_active=True).select_related("employee_work_info")
    if request.user.is_superuser or request.user.is_staff:
        return employees
    return employees.filter(employee_work_info__reporting_manager_id=manager)


def _workspace_context(request, manager):
    from base.models import JobPosition
    from leave.models import LeaveRequest, LeaveType
    from recruitment.models import Recruitment

    team = _team_members(request, manager)
    team_ids = team.values_list("id", flat=True)
    manager_candidates = Employee.objects.filter(is_active=True)
    if request.user.is_superuser or request.user.is_staff:
        manager_candidates = manager_candidates.exclude(pk=getattr(manager, "pk", None))
    else:
        manager_candidates = manager_candidates.exclude(id__in=team_ids)
    return {
        "is_manager": manager is not None,
        "team": team,
        "job_positions": JobPosition.objects.filter(is_active=True).order_by("job_position"),
        "leave_types": LeaveType.objects.filter(is_active=True).order_by("name"),
        "managers": manager_candidates.order_by("employee_first_name", "employee_last_name"),
        "requisitions": Recruitment.objects.filter(recruitment_managers=manager).order_by("-id")[:12] if manager else Recruitment.objects.none(),
        "team_leaves": LeaveRequest.objects.filter(employee_id__in=team_ids).select_related("employee_id", "leave_type_id").order_by("-start_date")[:20],
        "reporting_changes": ReportingManagerChangeRequest.objects.filter(current_manager_id=manager).select_related("employee_id", "requested_manager_id").order_by("-id")[:20] if manager else ReportingManagerChangeRequest.objects.none(),
    }


@login_required
def requests_view(request):
    manager = _manager_for(request)
    context = _workspace_context(request, manager)
    context["active_tab"] = request.GET.get("tab", "requisitions")
    return render(request, "requests/requests.html", context)


def _manager_required(request):
    manager = _manager_for(request)
    if not manager:
        messages.error(request, "Manager access is required for team requests.")
    return manager


@login_required
def create_job_requisition(request):
    if request.method != "POST" or not (manager := _manager_required(request)):
        return redirect("requests-view")
    from base.models import JobPosition
    from recruitment.models import Recruitment

    title, description = request.POST.get("title", "").strip(), request.POST.get("description", "").strip()
    try:
        vacancy = max(1, int(request.POST.get("vacancy", "1")))
    except ValueError:
        vacancy = 1
    if not title or not description:
        messages.error(request, "Add a role title and a short hiring brief.")
        return redirect("requests-view")
    requisition = Recruitment.objects.create(
        title=title, description=description, vacancy=vacancy,
        company_id=getattr(getattr(manager, "employee_work_info", None), "company_id", None),
        is_published=False, publish_in_linkedin=False, start_date=timezone.localdate(),
    )
    requisition.recruitment_managers.add(manager)
    if position := JobPosition.objects.filter(pk=request.POST.get("job_position_id")).first():
        requisition.open_positions.add(position)
    messages.success(request, "Draft job requisition created for HR review.")
    return redirect("requests-view")


@login_required
def create_team_leave_request(request):
    if request.method != "POST" or not (manager := _manager_required(request)):
        return redirect("requests-view")
    from leave.models import LeaveRequest, LeaveType

    employee = get_object_or_404(_team_members(request, manager), pk=request.POST.get("employee_id"))
    leave_type = get_object_or_404(LeaveType.objects.filter(is_active=True), pk=request.POST.get("leave_type_id"))
    try:
        start_date = parse_date(request.POST.get("start_date", ""))
        end_date = parse_date(request.POST.get("end_date", "")) or start_date
        if not start_date:
            raise ValueError("Choose a valid start date.")
        leave_request = LeaveRequest(
            employee_id=employee, leave_type_id=leave_type,
            start_date=start_date, end_date=end_date,
            start_date_breakdown="full_day", end_date_breakdown="full_day",
            description=request.POST.get("description", "").strip(),
            attachment=request.FILES.get("attachment"), created_by=manager,
        )
        leave_request.full_clean()
        leave_request.save()
    except (ValidationError, TypeError, ValueError) as error:
        messages.error(request, f"Leave request was not created: {error}")
    else:
        messages.success(request, "Team leave request submitted for approval.")
    return redirect("requests-view")


@login_required
def create_reporting_manager_change(request):
    if request.method != "POST" or not (manager := _manager_required(request)):
        return redirect("requests-view")
    member = get_object_or_404(_team_members(request, manager), pk=request.POST.get("employee_id"))
    new_manager = get_object_or_404(Employee.objects.filter(is_active=True).exclude(pk=member.pk), pk=request.POST.get("requested_manager_id"))
    reason = request.POST.get("reason", "").strip()
    if new_manager == manager:
        messages.error(request, "Choose a different reporting manager.")
    elif not reason:
        messages.error(request, "Add a reason for the reporting change.")
    else:
        ReportingManagerChangeRequest.objects.create(employee_id=member, current_manager_id=manager, requested_manager_id=new_manager, reason=reason, created_by=request.user)
        messages.success(request, "Reporting-manager change request submitted.")
    return redirect("requests-view")


@login_required
def decide_reporting_manager_change(request, pk, decision):
    if request.method != "POST" or not (request.user.is_superuser or request.user.is_staff):
        return HttpResponseForbidden("Only HR administrators can decide reporting changes.")
    change = get_object_or_404(ReportingManagerChangeRequest, pk=pk, status="requested")
    change.status, change.decision_note, change.modified_by = ("approved" if decision == "approve" else "declined"), request.POST.get("decision_note", "").strip(), request.user
    change.save()
    if change.status == "approved":
        work_info = change.employee_id.employee_work_info
        work_info.reporting_manager_id = change.requested_manager_id
        work_info.save(update_fields=["reporting_manager_id"])
    messages.success(request, f"Reporting change {change.status}.")
    return redirect("requests-view")


@login_required
def export_team_leave_requests(request, absences_only=False):
    manager = _manager_required(request)
    if not manager:
        return redirect("requests-view")
    from leave.models import LeaveRequest
    leave_requests = LeaveRequest.objects.filter(employee_id__in=_team_members(request, manager))
    if absences_only:
        leave_requests = leave_requests.exclude(status__in=["rejected", "cancelled"])
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="team-absences.csv"'
    writer = csv.writer(response)
    writer.writerow(["Employee", "Leave type", "Start", "End", "Days", "Status", "Reason"])
    for item in leave_requests.select_related("employee_id", "leave_type_id").order_by("-start_date"):
        writer.writerow([item.employee_id, item.leave_type_id, item.start_date, item.end_date, item.requested_days, item.status, item.description])
    return response


@login_required
@hx_request_required
def requests_shift_request_tab(request):
    return HttpResponseForbidden("Shift requests are not used by EvoluteHR.")


requests_shift_inbox_tab = requests_shift_request_tab
requests_work_type_tab = requests_shift_request_tab
requests_document_tab = requests_shift_request_tab
