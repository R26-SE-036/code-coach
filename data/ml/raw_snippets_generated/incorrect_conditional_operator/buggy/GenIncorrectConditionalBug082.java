public class GenIncorrectConditionalBug082 {
    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }

    static String describe2(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static void announce(int limit) {
        if (limit = 10) {
            System.out.println("hit the target");
        }
    }
}
