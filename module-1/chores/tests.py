from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
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

    def test_member_chore_and_weekly_round_identities_are_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            HouseholdMember.objects.create(name=self.alex.name)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Chore.objects.create(name=self.chore.name)

        with self.assertRaises(IntegrityError), transaction.atomic():
            WeeklyRound.objects.create(starts_on=self.first_week.starts_on)

    def test_status_assignment_constraint_covers_all_statuses(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RoundChore.objects.create(
                weekly_round=self.first_week,
                chore=self.chore,
                added_by=self.alex,
                assigned_to=self.alex,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RoundChore.objects.create(
                weekly_round=self.first_week,
                chore=self.chore,
                added_by=self.alex,
                status=RoundChore.Status.COMPLETED,
            )

        round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
            status=RoundChore.Status.ASSIGNED,
            assigned_to=self.alex,
        )

        self.assertEqual(round_chore.status, RoundChore.Status.ASSIGNED)
        self.assertEqual(round_chore.assigned_to, self.alex)

    def test_excluding_a_chore_from_a_round_preserves_its_record(self):
        round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
            status=RoundChore.Status.COMPLETED,
            assigned_to=self.alex,
        )

        round_chore.is_included = False
        round_chore.save()

        preserved_round_chore = RoundChore.objects.get(pk=round_chore.pk)
        self.assertFalse(preserved_round_chore.is_included)
        self.assertEqual(preserved_round_chore.weekly_round, self.first_week)
        self.assertEqual(preserved_round_chore.status, RoundChore.Status.COMPLETED)
        self.assertEqual(preserved_round_chore.assigned_to, self.alex)

    def test_readiness_and_selection_can_repeat_in_a_later_week(self):
        ReadinessConfirmation.objects.create(
            weekly_round=self.first_week,
            member=self.alex,
        )
        first_round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
        )
        ChoreSelection.objects.create(
            round_chore=first_round_chore,
            member=self.alex,
            phase=ChoreSelection.AllocationPhase.FIRST,
        )

        second_week = WeeklyRound.objects.create(starts_on=date(2026, 1, 12))
        ReadinessConfirmation.objects.create(
            weekly_round=second_week,
            member=self.alex,
        )
        second_round_chore = RoundChore.objects.create(
            weekly_round=second_week,
            chore=self.chore,
            added_by=self.alex,
        )
        ChoreSelection.objects.create(
            round_chore=second_round_chore,
            member=self.alex,
            phase=ChoreSelection.AllocationPhase.FIRST,
        )

        self.assertEqual(self.alex.readiness_confirmations.count(), 2)
        self.assertEqual(self.alex.chore_selections.count(), 2)

    def test_referenced_historical_records_are_protected_from_deletion(self):
        RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
            status=RoundChore.Status.COMPLETED,
            assigned_to=self.alex,
        )

        with self.assertRaises(ProtectedError):
            self.chore.delete()

        with self.assertRaises(ProtectedError):
            self.first_week.delete()

        with self.assertRaises(ProtectedError):
            self.alex.delete()

    def test_model_choices_reject_unknown_status_and_allocation_phase(self):
        invalid_status = RoundChore(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
            status="unknown",
            assigned_to=self.alex,
        )

        with self.assertRaises(ValidationError) as invalid_status_error:
            invalid_status.full_clean()

        self.assertIn("status", invalid_status_error.exception.message_dict)

        round_chore = RoundChore.objects.create(
            weekly_round=self.first_week,
            chore=self.chore,
            added_by=self.alex,
        )
        invalid_selection = ChoreSelection(
            round_chore=round_chore,
            member=self.alex,
            phase="unknown",
        )

        with self.assertRaises(ValidationError) as invalid_phase_error:
            invalid_selection.full_clean()

        self.assertIn("phase", invalid_phase_error.exception.message_dict)
