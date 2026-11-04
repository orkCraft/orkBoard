using System;

namespace Game.Core
{
    public class Rng
    {
        public int Next() => Random.Shared.Next();
    }
}
