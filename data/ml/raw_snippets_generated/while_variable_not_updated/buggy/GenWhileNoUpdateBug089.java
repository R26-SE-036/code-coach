public class GenWhileNoUpdateBug089 {
    static String describe1(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static void countdown(int attempts) {
        while (attempts > 0) {
            System.out.println("left: " + attempts);
        }
    }
}
