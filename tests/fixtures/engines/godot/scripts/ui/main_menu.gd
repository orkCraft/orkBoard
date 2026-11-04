extends Control

const OPTIONS = "res://scenes/options.tscn"
const Tuning = preload("res://scripts/game/tuning.gd")


func _on_start_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/level_1.tscn")


func _on_options_pressed() -> void:
	get_tree().change_scene_to_file(OPTIONS)
