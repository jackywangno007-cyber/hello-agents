extends Node

signal chat_response_received(response_data: Dictionary)
signal chat_error(message: String)
signal world_config_received(config_data: Dictionary)
signal world_config_error(message: String)

const API_BASE_URL := "http://127.0.0.1:8000"

var _chat_request: HTTPRequest = null
var _world_request: HTTPRequest = null
var _pending_npc_name: String = ""


func _ready() -> void:
	_chat_request = HTTPRequest.new()
	_chat_request.name = "ChatHTTPRequest"
	add_child(_chat_request)
	_chat_request.request_completed.connect(_on_chat_request_completed)

	_world_request = HTTPRequest.new()
	_world_request.name = "WorldHTTPRequest"
	add_child(_world_request)
	_world_request.request_completed.connect(_on_world_request_completed)

	print("[ApiClient] Ready. Base URL:", API_BASE_URL)


func send_chat_request(npc_name: String, message: String) -> void:
	if _chat_request.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		emit_signal("chat_error", "A chat request is already in progress.")
		return

	_pending_npc_name = npc_name
	var url: String = "%s/dialogue" % API_BASE_URL
	var headers: PackedStringArray = ["Content-Type: application/json"]
	var body: String = JSON.stringify({
		"npc_name": npc_name,
		"message": message,
		"user_message": message
	})
	print("[ApiClient] POST", url)
	print("[ApiClient] Body:", body)

	var error := _chat_request.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		emit_signal("chat_error", "Failed to start chat request: %s" % error)


func fetch_world_config() -> void:
	_send_world_request("%s/world-config" % API_BASE_URL, HTTPClient.METHOD_GET, "")


func save_world_config(config_data: Dictionary) -> void:
	var body := JSON.stringify(config_data)
	_send_world_request(
		"%s/world-config" % API_BASE_URL,
		HTTPClient.METHOD_POST,
		body
	)


func apply_world_preset(preset_id: String) -> void:
	_send_world_request(
		"%s/world-presets/%s" % [API_BASE_URL, preset_id],
		HTTPClient.METHOD_POST,
		""
	)


func _send_world_request(url: String, method: int, body: String) -> void:
	if _world_request.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		emit_signal("world_config_error", "A world config request is already in progress.")
		return

	var headers: PackedStringArray = ["Content-Type: application/json"]
	print("[ApiClient] WORLD", url)
	var error := _world_request.request(url, headers, method, body)
	if error != OK:
		emit_signal("world_config_error", "Failed to start world request: %s" % error)


func _on_chat_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var body_text := body.get_string_from_utf8()
	print("[ApiClient] Request completed. result=", result, " response_code=", response_code)
	print("[ApiClient] Response body:", body_text)

	if result != HTTPRequest.RESULT_SUCCESS:
		emit_signal("chat_error", "Network request failed. Result code: %s" % result)
		return

	if response_code < 200 or response_code >= 300:
		emit_signal("chat_error", _extract_error_message(response_code, body_text))
		return

	var parsed: Variant = JSON.parse_string(body_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		emit_signal("chat_error", "Failed to parse server response as JSON.")
		return

	var response_data: Dictionary = {
		"npc_name": str(parsed.get("npc_name", _pending_npc_name)),
		"npc_display_name": str(parsed.get("npc_display_name", _pending_npc_name)),
		"npc_role": str(parsed.get("npc_role", "")),
		"scene_title": str(parsed.get("scene_title", "")),
		"scene_theme": str(parsed.get("scene_theme", "")),
		"reply_text": str(parsed.get("reply_text", parsed.get("reply", ""))),
		"relationship_score": int(parsed.get("relationship_score", 50)),
		"relationship_stage": str(parsed.get("relationship_stage", "neutral")),
		"task_title": str(parsed.get("task_title", "No active task")),
		"task_status": str(parsed.get("task_status", "none")),
		"task_description": str(parsed.get("task_description", "")),
		"task_feedback": str(parsed.get("task_feedback", "")),
		"memory_highlights": parsed.get("memory_highlights", [])
	}

	if response_data["reply_text"] == "":
		emit_signal("chat_error", "Server response does not contain a reply field.")
		return

	emit_signal("chat_response_received", response_data)


func _on_world_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var body_text := body.get_string_from_utf8()
	print("[ApiClient] World response completed. result=", result, " response_code=", response_code)
	print("[ApiClient] World response body:", body_text)

	if result != HTTPRequest.RESULT_SUCCESS:
		emit_signal("world_config_error", "World request failed. Result code: %s" % result)
		return

	if response_code < 200 or response_code >= 300:
		emit_signal("world_config_error", _extract_error_message(response_code, body_text))
		return

	var parsed: Variant = JSON.parse_string(body_text)
	if typeof(parsed) != TYPE_DICTIONARY:
		emit_signal("world_config_error", "Failed to parse world config JSON.")
		return

	emit_signal("world_config_received", parsed)


func _extract_error_message(response_code: int, body_text: String) -> String:
	var server_message: String = "Server returned HTTP %s" % response_code
	var parsed_error: Variant = JSON.parse_string(body_text)
	if typeof(parsed_error) == TYPE_DICTIONARY and parsed_error.has("detail"):
		server_message = "%s: %s" % [server_message, str(parsed_error["detail"])]
	return server_message
