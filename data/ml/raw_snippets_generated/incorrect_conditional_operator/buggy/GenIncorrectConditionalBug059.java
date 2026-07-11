public class GenIncorrectConditionalBug059 {
    static boolean matches(boolean armed, boolean verified) {
        if (armed = verified) {
            return true;
        }
        return false;
    }
}
