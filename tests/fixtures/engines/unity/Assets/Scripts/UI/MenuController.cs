using UnityEngine;
using UnityEngine.SceneManagement;
using Game.Gameplay;

namespace Game.UI
{
    public class MenuController : MonoBehaviour
    {
        void Play() { SceneManager.LoadScene("Level1"); }
    }
}
