extends CharacterBody2D

@export var npc_id: String = "Alice"

const NPC_TEXTURES := {
	"Alice": preload("res://assets/characters/alice_badge.svg"),
	"Bob": preload("res://assets/characters/bob_badge.svg"),
	"Charlie": preload("res://assets/characters/charlie_badge.svg")
}

const NPC_COLORS := {
	"Alice": Color("f6c56b"),
	"Bob": Color("b4cee7"),
	"Charlie": Color("cad88a")
}

var display_name: String = ""
var role_text: String = ""

@onready var interaction_area: Area2D = $InteractionArea
@onready var portrait: Sprite2D = $Portrait
@onready var name_label: Label = $NamePlate/NameLabel
@onready var role_label: Label = $NamePlate/RoleLabel
@onready var prompt_label: Control = $PromptLabel


func _ready() -> void:
	_apply_default_profile()
	prompt_label.visible = false
	interaction_area.body_entered.connect(_on_interaction_area_body_entered)
	interaction_area.body_exited.connect(_on_interaction_area_body_exited)


func get_npc_id() -> String:
	return npc_id


func get_npc_display_name() -> String:
	return display_name


func get_npc_role() -> String:
	return role_text


func apply_world_profile(profile: Dictionary) -> void:
	display_name = str(profile.get("name", npc_id))
	role_text = str(profile.get("role", "Resident"))
	name_label.text = display_name
	role_label.text = role_text
	name_label.modulate = NPC_COLORS.get(npc_id, Color.WHITE)

	if NPC_TEXTURES.has(npc_id):
		portrait.texture = NPC_TEXTURES[npc_id]


func _apply_default_profile() -> void:
	apply_world_profile(
		{
			"name": npc_id,
			"role": "Resident"
		}
	)


func _on_interaction_area_body_entered(body: Node) -> void:
	if body.has_method("set_nearby_npc"):
		body.set_nearby_npc(self)
		prompt_label.visible = true


func _on_interaction_area_body_exited(body: Node) -> void:
	if body.has_method("clear_nearby_npc"):
		body.clear_nearby_npc(self)
		prompt_label.visible = false
