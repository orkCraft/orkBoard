extends Control

var settings := Settings.new()


func _on_back_pressed() -> void:
	get_tree().change_scene_to_packed(preload("res://scenes/main_menu.tscn"))
	print(Settings.volume)
