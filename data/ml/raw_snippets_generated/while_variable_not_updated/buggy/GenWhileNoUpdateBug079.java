public class GenWhileNoUpdateBug079 {
    static String describe1(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe2(int limit) {
        if (limit < 5) {
            return "low";
        } else if (limit > 20) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven3(int limit) {
        return limit % 2 == 0;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
        }
    }
}
