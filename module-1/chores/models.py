from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class HouseholdMember(models.Model):
    """A person in the single shared household."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WeeklyRound(models.Model):
    """A Monday-to-Sunday planning period."""

    starts_on = models.DateField(unique=True)

    class Meta:
        ordering = ["-starts_on"]

    def clean(self):
        super().clean()
        if self.starts_on and self.starts_on.weekday() != 0:
            raise ValidationError({"starts_on": "A weekly round must start on a Monday."})

    def __str__(self):
        return f"Week of {self.starts_on:%Y-%m-%d}"


class Chore(models.Model):
    """A reusable household chore, independent of any particular week."""

    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoundChore(models.Model):
    """The state of one chore in one weekly round."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        COMPLETED = "completed", "Completed"

    weekly_round = models.ForeignKey(
        WeeklyRound,
        on_delete=models.PROTECT,
        related_name="round_chores",
    )
    chore = models.ForeignKey(
        Chore,
        on_delete=models.PROTECT,
        related_name="round_chores",
    )
    added_by = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        related_name="added_round_chores",
    )
    is_included = models.BooleanField(default=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    assigned_to = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        related_name="assigned_round_chores",
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["weekly_round", "chore"],
                name="unique_chore_per_weekly_round",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="pending", assigned_to__isnull=True)
                    | Q(status="assigned", assigned_to__isnull=False)
                    | Q(status="completed", assigned_to__isnull=False)
                ),
                name="round_chore_status_matches_assignment",
            ),
        ]
        ordering = ["chore__name"]

    def __str__(self):
        return f"{self.chore} ({self.weekly_round})"


class ReadinessConfirmation(models.Model):
    """A member's confirmation that a weekly round can enter allocation."""

    weekly_round = models.ForeignKey(
        WeeklyRound,
        on_delete=models.PROTECT,
        related_name="readiness_confirmations",
    )
    member = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        related_name="readiness_confirmations",
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["weekly_round", "member"],
                name="unique_readiness_confirmation_per_member_and_round",
            ),
        ]


class ChoreSelection(models.Model):
    """One member's choice of a chore during an allocation phase."""

    class AllocationPhase(models.TextChoices):
        FIRST = "first", "First allocation round"
        SECOND = "second", "Second allocation round"

    round_chore = models.ForeignKey(
        RoundChore,
        on_delete=models.PROTECT,
        related_name="selections",
    )
    member = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        related_name="chore_selections",
    )
    phase = models.CharField(max_length=6, choices=AllocationPhase.choices)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["round_chore", "member", "phase"],
                name="unique_chore_selection_per_member_and_phase",
            ),
        ]
