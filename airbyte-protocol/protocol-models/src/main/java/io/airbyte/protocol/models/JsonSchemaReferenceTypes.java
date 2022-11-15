package io.airbyte.protocol.models;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import java.util.Map;
import java.util.Set;

public class JsonSchemaReferenceTypes {

  public static final Set<String> PRIMITIVE_JSON_TYPES = ImmutableSet.of(
      "string",
      "number",
      "integer",
      "boolean"
  );
  public static final Map<String, String> AIRBYTE_TYPE_TO_REFERENCE_TYPE = ImmutableMap.of(
      "timestamp_with_timezone", "WellKnownTypes.json#definitions/TimestampWithTimezone",
      "timestamp_without_timezone", "WellKnownTypes.json#definitions/TimestampWithoutTimezone",
      "time_with_timezone", "WellKnownTypes.json#definitions/TimeWithTimezone",
      "time_without_timezone", "WellKnownTypes.json#definitions/TimeWithoutTimezone",
      "integer", "WellKnownTypes.json#definitions/Integer",
      // these types never actually use airbyte_type, but including them for consistency
      "string", "WellKnownTypes.json#definitions/String",
      "number", "WellKnownTypes.json#definitions/Number",
      "boolean", "WellKnownTypes.json#definitions/Boolean",
      "date", "WellKnownTypes.json#definitions/Date"
  );
}
