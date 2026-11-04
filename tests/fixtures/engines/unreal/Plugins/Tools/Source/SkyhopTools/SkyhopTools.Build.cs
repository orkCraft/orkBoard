using UnrealBuildTool;

public class SkyhopTools : ModuleRules
{
    public SkyhopTools(ReadOnlyTargetRules Target) : base(Target)
    {
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "Inventory" });
    }
}
