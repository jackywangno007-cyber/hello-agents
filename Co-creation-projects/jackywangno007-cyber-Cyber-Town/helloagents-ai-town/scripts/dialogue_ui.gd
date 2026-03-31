extends CanvasLayer

var current_npc_id: String = ""
var current_npc_display_name: String = ""
var current_npc_role: String = ""
var current_relationship_score: int = 0
var current_relationship_stage: String = ""
var player: Node = null
var api_client: Node = null

@onready var root_control: Control = $Root
@onready var npc_name_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/HeaderRow/HeaderText/NPCNameLabel
@onready var npc_hint_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/HeaderRow/HeaderText/NPCHintLabel
@onready var relationship_stage_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/RelationshipCard/MarginContainer/VBoxContainer/RelationshipStageLabel
@onready var relationship_score_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/RelationshipCard/MarginContainer/VBoxContainer/RelationshipScoreLabel
@onready var task_title_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/TaskCard/MarginContainer/VBoxContainer/TaskTitleLabel
@onready var task_status_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/TaskCard/MarginContainer/VBoxContainer/TaskStatusLabel
@onready var task_description_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/TaskCard/MarginContainer/VBoxContainer/TaskDescriptionLabel
@onready var task_feedback_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/InfoRow/TaskCard/MarginContainer/VBoxContainer/TaskFeedbackLabel
@onready var memory_highlights_label: RichTextLabel = $Root/PanelContainer/MarginContainer/MainColumn/MemoryCard/MarginContainer/MemoryHighlightsLabel
@onready var dialogue_log: RichTextLabel = $Root/PanelContainer/MarginContainer/MainColumn/ChatCard/MarginContainer/DialogueLog
@onready var message_input: LineEdit = $Root/PanelContainer/MarginContainer/MainColumn/InputRow/MessageInput
@onready var send_button: Button = $Root/PanelContainer/MarginContainer/MainColumn/InputRow/ButtonRow/SendButton
@onready var close_button: Button = $Root/PanelContainer/MarginContainer/MainColumn/InputRow/ButtonRow/CloseButton


func _ready() -> void:
	hide()
	root_control.mouse_filter = Control.MOUSE_FILTER_STOP
	send_button.pressed.connect(_on_send_button_pressed)
	close_button.pressed.connect(_on_close_button_pressed)
	message_input.text_submitted.connect(_on_message_submitted)

	api_client = get_node_or_null("/root/ApiClient")
	if api_client == null:
		append_system_message("System: ApiClient autoload is missing.")
		return

	api_client.chat_response_received.connect(_on_chat_response_received)
	api_client.chat_error.connect(_on_chat_error)
	_reset_status_view()


func start_dialogue(npc_id: String, display_name: String, role_text: String) -> void:
	current_npc_id = npc_id
	current_npc_display_name = display_name
	current_npc_role = role_text
	current_relationship_score = 0
	current_relationship_stage = ""
	npc_name_label.text = "Talking to %s" % display_name
	npc_hint_label.text = "%s - %s" % [display_name, role_text]
	dialogue_log.clear()
	append_system_message("Dialogue opened. Chat to influence relationship, memory, and tasks.")
	message_input.text = ""
	set_waiting_state(false)
	_reset_status_view()
	show()
	message_input.grab_focus()


func _on_send_button_pressed() -> void:
	var text := message_input.text.strip_edges()
	if text.is_empty():
		return

	append_player_message(text)
	message_input.text = ""
	set_waiting_state(true)

	if api_client == null:
		_on_chat_error("ApiClient autoload is missing.")
		return

	api_client.send_chat_request(current_npc_id, text)


func _on_message_submitted(_new_text: String) -> void:
	_on_send_button_pressed()


func _on_chat_response_received(response_data: Dictionary) -> void:
	var npc_id := str(response_data.get("npc_name", ""))
	if npc_id != current_npc_id:
		return

	current_npc_display_name = str(response_data.get("npc_display_name", current_npc_display_name))
	current_npc_role = str(response_data.get("npc_role", current_npc_role))
	current_relationship_score = int(response_data.get("relationship_score", 50))
	current_relationship_stage = str(response_data.get("relationship_stage", "neutral"))

	npc_name_label.text = "Talking to %s" % current_npc_display_name
	npc_hint_label.text = "%s - %s" % [current_npc_display_name, current_npc_role]
	_refresh_relationship_status()
	_refresh_task_status(
		str(response_data.get("task_title", "No active task")),
		str(response_data.get("task_status", "none")),
		str(response_data.get("task_description", "")),
		str(response_data.get("task_feedback", ""))
	)

	var highlights: Array[String] = []
	var highlights_variant: Variant = response_data.get("memory_highlights", [])
	if typeof(highlights_variant) == TYPE_ARRAY:
		for item in highlights_variant:
			highlights.append(_truncate_text(str(item), 56))
	_refresh_memory_highlights(highlights)

	append_npc_message(current_npc_display_name, str(response_data.get("reply_text", "")))
	set_waiting_state(false)
	message_input.grab_focus()


func _on_chat_error(message: String) -> void:
	append_system_message("System: %s" % message)
	set_waiting_state(false)
	message_input.grab_focus()


func _on_close_button_pressed() -> void:
	close_dialogue()


func close_dialogue() -> void:
	hide()
	current_npc_id = ""
	current_npc_display_name = ""
	current_npc_role = ""
	current_relationship_score = 0
	current_relationship_stage = ""
	message_input.text = ""
	set_waiting_state(false)
	_reset_status_view()

	if player != null and player.has_method("set_interacting"):
		player.set_interacting(false)


func set_waiting_state(waiting: bool) -> void:
	message_input.editable = not waiting
	send_button.disabled = waiting
	send_button.text = "Sending..." if waiting else "Send"


func append_player_message(message: String) -> void:
	dialogue_log.append_text("You: %s\n" % _truncate_text(message, 80))


func append_npc_message(display_name: String, message: String) -> void:
	dialogue_log.append_text("%s: %s\n" % [display_name, _truncate_text(message, 220)])


func append_system_message(message: String) -> void:
	dialogue_log.append_text("%s\n" % _truncate_text(message, 120))


func _reset_status_view() -> void:
	relationship_stage_label.text = "Relationship: --"
	relationship_score_label.text = "Affinity: -- / 100"
	task_title_label.text = "Task: No active task"
	task_status_label.text = "Status: Locked"
	task_description_label.text = "Task details will appear here when the current NPC unlocks them."
	task_feedback_label.text = ""
	_refresh_memory_highlights([])


func _refresh_relationship_status() -> void:
	relationship_stage_label.text = "Relationship: %s" % current_relationship_stage.capitalize()
	relationship_score_label.text = "Affinity: %d / 100" % current_relationship_score


func _refresh_task_status(title: String, status: String, description: String, feedback: String) -> void:
	task_title_label.text = "Task: %s" % _truncate_text(title, 34)
	task_status_label.text = "Status: %s" % status.replace("_", " ").capitalize()
	task_description_label.text = "Task Details: %s" % _truncate_text(description, 88)
	task_feedback_label.text = "" if feedback.strip_edges().is_empty() else "Latest Update: %s" % _truncate_text(feedback, 88)


func _refresh_memory_highlights(highlights: Array[String]) -> void:
	memory_highlights_label.clear()
	memory_highlights_label.append_text("Key Memories\n")
	if highlights.is_empty():
		memory_highlights_label.append_text("- No major memories yet.\n")
		return

	for item in highlights.slice(0, 3):
		memory_highlights_label.append_text("- %s\n" % item)


func _truncate_text(text: String, max_length: int) -> String:
	if text.length() <= max_length:
		return text
	return "%s..." % text.substr(0, max_length)
