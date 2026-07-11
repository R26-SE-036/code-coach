public class GenIncorrectConditionalFix005 {
    static boolean matches(boolean enabled, boolean loaded) {
        if (enabled == loaded) {
            return true;
        }
        return false;
    }
}
