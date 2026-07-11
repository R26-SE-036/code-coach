public class GenWhileNoUpdateFix041 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void pump(boolean ready, int attempts) {
        while (!ready) {
            System.out.println(attempts);
            attempts++;
            ready = attempts > 10;
        }
    }

    static void printAll2(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
