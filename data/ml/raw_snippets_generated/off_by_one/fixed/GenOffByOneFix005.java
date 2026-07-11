public class GenOffByOneFix005 {
    static int addUp(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static boolean isEven1(int points) {
        return points % 2 == 0;
    }

    static String describe2(int points) {
        if (points < 5) {
            return "low";
        } else if (points > 20) {
            return "high";
        }
        return "medium";
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum4(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static void printAll5(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }
}
