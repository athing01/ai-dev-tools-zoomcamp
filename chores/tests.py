from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import (
    Chore,
    ChoreSelection,
    HouseholdMember,
    ReadinessConfirmation,
    RoundChore,
    WeeklyRound,
)


class ChoresModelTests(TestCase):
    def setUp(self):
        self.alex = HouseholdMember.objects.create(name="Alex")
        self.blair = HouseholdMember.objects.create(name="Blair")
        self.chore = Chore.objects.create(name="Wash dishes")
        self.first_week = WeeklyRound.objects.create(starts_on=date(2026, 1, 5))

    def test_weekly_round_must_start_on_monday(self):
        round_ = WeeklyRound(starts_on=date(2026, 1, 6))

        with self.assertRaises(ValidationError):
            round_.full_clean()

    def test_round_chore_keeps_each_weeks_state_separate(self):
        first_round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
            status=RoundChore.Status.COMPLETED,
            assigned_to=self.alex,
        )
        second_week = WeeklyRound.objects.create(starts_on=date(2026, 1, 12))
        second_round_chore = RoundChore.objects.create(
            weekly_round=second_week,
            chore=self.chore,
            added_by=self.alex,
        )

        self.assertEqual(first_round_chore.status, RoundChore.Status.COMPLETED)
        self.assertEqual(second_round_chore.status, RoundChore.Status.PENDING)
        self.assertIsNone(second_round_chore.assigned_to)

    def test_a_chore_can_only_appear_once_in_a_weekly_round(self):
        RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
        )

        with self.assertRaises(IntegrityError):
            RoundChore.objects.create(
                weekly_round=self.first_week,
                chore=self.chore,
                added_by=self.blair,
            )

    def test_assignment_status_must_match_assignee(self):
        with self.assertRaises(IntegrityError):
            RoundChore.objects.create(
                weekly_round=self.first_week,
                chore=self.chore,
                added_by=self.alex,
                status=RoundChore.Status.ASSIGNED,
            )

    def test_readiness_confirmation_is_unique_per_member_and_round(self):
        ReadinessConfirmation.objects.create(
            weekly_round=self.first_week,
            member=self.alex,
        )

        with self.assertRaises(IntegrityError):
            ReadinessConfirmation.objects.create(
                weekly_round=self.first_week,
                member=self.alex,
            )

    def test_selection_is_unique_per_phase_but_can_be_repeated_next_phase(self):
        round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
        )
        ChoreSelection.objects.create(
            round_chore=round_chore,
            member=self.alex,
            phase=ChoreSelection.AllocationPhase.FIRST,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ChoreSelection.objects.create(
                round_chore=round_chore,
                member=self.alex,
                phase=ChoreSelection.AllocationPhase.FIRST,
            )

        ChoreSelection.objects.create(
            round_chore=round_chore,
            member=self.alex,
            phase=ChoreSelection.AllocationPhase.SECOND,
        )

        self.assertEqual(round_chore.selections.count(), 2)
