public class GenIncorrectConditionalFix142 {
    static boolean matches(boolean armed, boolean done) {
        if (armed == done) {
            return true;
        }
        return false;
    }
}
