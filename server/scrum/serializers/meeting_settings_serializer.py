from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from scrum.models import ProjectMeetingSettings


class ProjectMeetingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMeetingSettings
        fields = (
            'id',
            'project_id',
            'meeting_days',
            'meeting_time',
            'timezone',
            'google_meet_link',
            'weekly_goals',
            'monthly_goals',
            'alert_minutes_before',
            'is_active',
            'last_reminder_sent_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'project_id', 'last_reminder_sent_at', 'created_at', 'updated_at')

    def validate_meeting_days(self, value):
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        if not isinstance(value, list):
            raise serializers.ValidationError('Meeting days must be a list')

        normalized_days = []
        seen_days = set()
        for day in value:
            normalized_day = str(day).strip().lower()
            if normalized_day not in valid_days:
                raise serializers.ValidationError('Meeting days must use full weekday names')
            if normalized_day not in seen_days:
                normalized_days.append(normalized_day)
                seen_days.add(normalized_day)

        if not normalized_days:
            raise serializers.ValidationError('At least one meeting day is required')

        return normalized_days

    def validate_timezone(self, value):
        timezone_name = value.strip()
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError('Timezone must be a valid IANA timezone') from exc
        return timezone_name
