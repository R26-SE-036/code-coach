public class GenIncorrectConditionalFix130 {
    static boolean matches(boolean active, boolean enabled) {
        if (active == enabled) {
            return true;
        }
        return false;
    }
}
