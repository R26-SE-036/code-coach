public class GenIncorrectConditionalBug089 {
    static boolean matches(boolean verified, boolean running) {
        if (verified = running) {
            return true;
        }
        return false;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
