extends Node2D

@onready var player: CharacterBody2D = $Player
@onready var dialogue_ui: CanvasLayer = $DialogueUI
@onready var top_bar_title: Label = $HUDRoot/TopBar/TopBarMargin/TopBarColumn/TopBarTitle
@onready var top_bar_hint: Label = $HUDRoot/TopBar/TopBarMargin/TopBarColumn/TopBarHint
@onready var world_button: Button = $HUDRoot/WorldButton
@onready var world_editor: CanvasLayer = $WorldEditor
@onready var npc_alice: Node = $NPC_Alice
@onready var npc_bob: Node = $NPC_Bob
@onready var npc_charlie: Node = $NPC_Charlie

var api_client: Node = null


func _ready() -> void:
	player.dialogue_ui = dialogue_ui
	dialogue_ui.player = player

	api_client = get_node_or_null("/root/ApiClient")
	if api_client == null:
		top_bar_hint.text = "ApiClient missing"
		return

	world_button.pressed.connect(_on_world_button_pressed)
	world_editor.save_requested.connect(_on_world_save_requested)
	world_editor.preset_requested.connect(_on_world_preset_requested)

	api_client.world_config_received.connect(_on_world_config_received)
	api_client.world_config_error.connect(_on_world_config_error)

	world_editor.show_status("Loading current world...")
	api_client.fetch_world_config()


func _on_world_button_pressed() -> void:
	world_editor.toggle_panel()


func _on_world_save_requested(config_data: Dictionary) -> void:
	world_editor.show_status("Saving world...")
	api_client.save_world_config(config_data)


func _on_world_preset_requested(preset_id: String) -> void:
	world_editor.show_status("Applying preset: %s" % preset_id)
	api_client.apply_world_preset(preset_id)


func _on_world_config_received(config_data: Dictionary) -> void:
	_apply_world_config(config_data)
	world_editor.show_status("World synced.")


func _on_world_config_error(message: String) -> void:
	world_editor.show_status("World config error: %s" % message)


func _apply_world_config(config_data: Dictionary) -> void:
	top_bar_title.text = str(config_data.get("scene_title", "Cyber Town"))
	top_bar_hint.text = _truncate_text(str(config_data.get("scene_theme", "")), 44)

	var npc_profiles: Dictionary = config_data.get("npcs", {})
	npc_alice.apply_world_profile(npc_profiles.get("Alice", {}))
	npc_bob.apply_world_profile(npc_profiles.get("Bob", {}))
	npc_charlie.apply_world_profile(npc_profiles.get("Charlie", {}))

	world_editor.apply_world_config(config_data)


func _truncate_text(text: String, max_length: int) -> String:
	if text.length() <= max_length:
		return text
	return "%s..." % text.substr(0, max_length)
