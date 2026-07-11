public class GenWhileNoUpdateFix099 {
    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
            level--;
        }
    }

    static String describe1(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }
}
