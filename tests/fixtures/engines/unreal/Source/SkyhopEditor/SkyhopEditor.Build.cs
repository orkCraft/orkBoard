using UnrealBuildTool;

public class SkyhopEditor : ModuleRules
{
    public SkyhopEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "Engine", "UnrealEd", "Skyhop" });
    }
}
