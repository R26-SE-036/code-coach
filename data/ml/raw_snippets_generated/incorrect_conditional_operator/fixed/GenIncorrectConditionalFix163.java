public class GenIncorrectConditionalFix163 {
    static boolean matches(boolean armed, boolean loaded) {
        if (armed == loaded) {
            return true;
        }
        return false;
    }
}
