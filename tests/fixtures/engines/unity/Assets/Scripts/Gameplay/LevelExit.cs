using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Gameplay
{
    public class LevelExit : MonoBehaviour
    {
        void Done() { SceneManager.LoadScene(0); }
    }
}
