using UnrealBuildTool;

public class Skyhop : ModuleRules
{
    public Skyhop(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "Inventory" });
        PrivateDependencyModuleNames.Add("Slate");
        PrivateDependencyModuleNames.AddRange(new string[] { "SkyhopTools" });
    }
}
