from rest_framework import serializers
from auditlog.models import LogEntry
import json

from rest_framework import serializers
from auditlog.models import LogEntry

class LogEntrySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    detials = serializers.SerializerMethodField()


    class Meta:
        model = LogEntry
        fields = ['user','action','timestamp','type','detials']  # শুধু এই field রিটার্ন হবে

    def get_user(self, obj):
        changes = obj.changes or {}
        if changes.get("data"):
            if isinstance(changes.get("data")[1], str):
                data_dict = json.loads(changes.get("data")[1])
                if data_dict.get("name") is not None:
                    name = data_dict.get("name")
                    return name
    def get_action(self, obj):
        action_map = {
            0: "Created",
            1: "Updated",
            2: "Deleted",
        }
        return action_map.get(obj.action, "Unknown")
    def get_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M")
    def get_type(self, obj):
        type_map = {
            0: "upload",
            1: "edit",
            2: "delete",
        }
        return type_map.get(obj.action, "other")
    def get_detials(self, obj):
        return obj.object_repr