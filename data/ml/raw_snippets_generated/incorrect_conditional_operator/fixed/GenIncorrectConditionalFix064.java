public class GenIncorrectConditionalFix064 {
    static boolean matches(boolean armed, boolean valid) {
        if (armed == valid) {
            return true;
        }
        return false;
    }
}
