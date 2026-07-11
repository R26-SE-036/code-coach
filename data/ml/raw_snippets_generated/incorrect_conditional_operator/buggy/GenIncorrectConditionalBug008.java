public class GenIncorrectConditionalBug008 {
    static String describe1(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean done, boolean open) {
        if (done = open) {
            return true;
        }
        return false;
    }
}
