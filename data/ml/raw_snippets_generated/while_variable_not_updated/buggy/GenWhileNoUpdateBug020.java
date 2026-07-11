public class GenWhileNoUpdateBug020 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static boolean isEven3(int quota) {
        return quota % 2 == 0;
    }

    static boolean isEven4(int stock) {
        return stock % 2 == 0;
    }

    static void countdown(int limit) {
        while (limit > 0) {
            System.out.println("left: " + limit);
        }
    }
}
