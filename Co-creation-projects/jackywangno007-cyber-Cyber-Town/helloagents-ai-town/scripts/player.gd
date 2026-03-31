extends CharacterBody2D

@export var move_speed: float = 220.0

var nearby_npc: Node = null
var interacting: bool = false
var dialogue_ui: CanvasLayer = null

@onready var portrait: Sprite2D = $Portrait


func _physics_process(_delta: float) -> void:
	if interacting:
		velocity = Vector2.ZERO
		move_and_slide()
		return

	var input_direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = input_direction * move_speed

	if absf(input_direction.x) > 0.05:
		portrait.flip_h = input_direction.x < 0.0

	move_and_slide()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact") and nearby_npc != null and dialogue_ui != null and not interacting:
		interacting = true
		dialogue_ui.start_dialogue(
			nearby_npc.get_npc_id(),
			nearby_npc.get_npc_display_name(),
			nearby_npc.get_npc_role()
		)


func set_nearby_npc(npc: Node) -> void:
	nearby_npc = npc


func clear_nearby_npc(npc: Node) -> void:
	if nearby_npc == npc:
		nearby_npc = null


func set_interacting(value: bool) -> void:
	interacting = value
