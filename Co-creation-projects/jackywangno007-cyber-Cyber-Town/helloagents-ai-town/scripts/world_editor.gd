extends CanvasLayer

signal save_requested(config_data: Dictionary)
signal preset_requested(preset_id: String)
signal close_requested()

@onready var root: Control = $Root
@onready var preset_option: OptionButton = $Root/PanelContainer/MarginContainer/MainColumn/PresetRow/PresetOption
@onready var status_label: Label = $Root/PanelContainer/MarginContainer/MainColumn/StatusLabel
@onready var scene_title_edit: LineEdit = $Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/SceneSection/MarginContainer/VBoxContainer/SceneTitleEdit
@onready var scene_theme_edit: LineEdit = $Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/SceneSection/MarginContainer/VBoxContainer/SceneThemeEdit
@onready var scene_description_edit: TextEdit = $Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/SceneSection/MarginContainer/VBoxContainer/SceneDescriptionEdit
@onready var scene_theme_prompt_edit: LineEdit = $Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/SceneSection/MarginContainer/VBoxContainer/SceneThemePromptEdit
@onready var save_button: Button = $Root/PanelContainer/MarginContainer/MainColumn/ButtonRow/SaveButton
@onready var close_button: Button = $Root/PanelContainer/MarginContainer/MainColumn/ButtonRow/CloseButton
@onready var apply_preset_button: Button = $Root/PanelContainer/MarginContainer/MainColumn/PresetRow/ApplyPresetButton


func _ready() -> void:
	root.visible = false
	save_button.pressed.connect(_on_save_button_pressed)
	close_button.pressed.connect(_on_close_button_pressed)
	apply_preset_button.pressed.connect(_on_apply_preset_button_pressed)


func toggle_panel() -> void:
	root.visible = not root.visible


func hide_panel() -> void:
	root.visible = false


func apply_world_config(config: Dictionary) -> void:
	scene_title_edit.text = str(config.get("scene_title", ""))
	scene_theme_edit.text = str(config.get("scene_theme", ""))
	scene_description_edit.text = str(config.get("scene_description", ""))
	scene_theme_prompt_edit.text = str(config.get("scene_theme_prompt", ""))

	var npcs: Dictionary = config.get("npcs", {})
	_apply_npc_fields("Alice", npcs.get("Alice", {}))
	_apply_npc_fields("Bob", npcs.get("Bob", {}))
	_apply_npc_fields("Charlie", npcs.get("Charlie", {}))
	set_presets(config.get("presets", []), str(config.get("preset_id", "")))


func set_presets(presets: Array, current_preset_id: String) -> void:
	preset_option.clear()
	for index in range(presets.size()):
		var preset: Dictionary = presets[index]
		preset_option.add_item(str(preset.get("scene_title", preset.get("preset_id", "Preset"))))
		preset_option.set_item_metadata(index, str(preset.get("preset_id", "")))
		if str(preset.get("preset_id", "")) == current_preset_id:
			preset_option.select(index)


func show_status(message: String) -> void:
	status_label.text = message


func _on_save_button_pressed() -> void:
	emit_signal("save_requested", _collect_config())


func _on_close_button_pressed() -> void:
	hide_panel()
	emit_signal("close_requested")


func _on_apply_preset_button_pressed() -> void:
	var selected_index := preset_option.get_selected_id()
	if selected_index < 0:
		return

	var preset_id := str(preset_option.get_item_metadata(selected_index))
	emit_signal("preset_requested", preset_id)


func _collect_config() -> Dictionary:
	return {
		"scene_title": scene_title_edit.text.strip_edges(),
		"scene_theme": scene_theme_edit.text.strip_edges(),
		"scene_description": scene_description_edit.text.strip_edges(),
		"scene_theme_prompt": scene_theme_prompt_edit.text.strip_edges(),
		"npcs": {
			"Alice": _collect_npc_fields("Alice"),
			"Bob": _collect_npc_fields("Bob"),
			"Charlie": _collect_npc_fields("Charlie")
		}
	}


func _apply_npc_fields(npc_id: String, profile: Dictionary) -> void:
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/NameEdit" % npc_id).text = str(profile.get("name", npc_id))
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/RoleEdit" % npc_id).text = str(profile.get("role", ""))
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/PersonalityEdit" % npc_id).text = str(profile.get("personality", ""))
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/SpeakingStyleEdit" % npc_id).text = str(profile.get("speaking_style", ""))
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/AvatarPromptEdit" % npc_id).text = str(profile.get("avatar_prompt", ""))
	get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/BuildingPromptEdit" % npc_id).text = str(profile.get("building_prompt", ""))


func _collect_npc_fields(npc_id: String) -> Dictionary:
	return {
		"id": npc_id,
		"name": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/NameEdit" % npc_id).text.strip_edges(),
		"role": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/RoleEdit" % npc_id).text.strip_edges(),
		"personality": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/PersonalityEdit" % npc_id).text.strip_edges(),
		"speaking_style": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/SpeakingStyleEdit" % npc_id).text.strip_edges(),
		"avatar_prompt": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/AvatarPromptEdit" % npc_id).text.strip_edges(),
		"building_prompt": get_node("Root/PanelContainer/MarginContainer/MainColumn/ScrollContainer/Fields/%sSection/MarginContainer/VBoxContainer/BuildingPromptEdit" % npc_id).text.strip_edges()
	}
