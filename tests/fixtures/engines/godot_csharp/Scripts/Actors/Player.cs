using Godot;
using Game.Core;

namespace Game.Actors;

public partial class Player : CharacterBody2D
{
    private readonly Rng _rng = new();
}
