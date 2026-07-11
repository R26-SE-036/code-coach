public class GenIncorrectConditionalFix101 {
    static boolean matches(boolean active, boolean loaded) {
        if (active == loaded) {
            return true;
        }
        return false;
    }
}
