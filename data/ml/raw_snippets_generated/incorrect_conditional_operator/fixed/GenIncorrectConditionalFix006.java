public class GenIncorrectConditionalFix006 {
    static boolean matches(boolean armed, boolean ready) {
        if (armed == ready) {
            return true;
        }
        return false;
    }
}
