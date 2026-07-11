public class GenCleanTailIndex028 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int tail(int[] scores) {
        return scores[scores.length - 1];
    }

    static boolean isEven2(int limit) {
        return limit % 2 == 0;
    }

    static void printAll3(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static boolean isEven5(int steps) {
        return steps % 2 == 0;
    }

    static int sum6(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static void printAll7(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static String join8(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
