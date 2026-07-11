public class GenIncorrectConditionalBug050 {
    static boolean matches(boolean verified, boolean active) {
        if (verified = active) {
            return true;
        }
        return false;
    }
}
