public class GenIncorrectConditionalFix076 {
    static boolean matches(boolean loaded, boolean ready) {
        if (loaded == ready) {
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
