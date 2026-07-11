public class GenWhileNoUpdateFix168 {
    static boolean isEven1(int count) {
        return count % 2 == 0;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void pump(boolean armed, int quota) {
        while (!armed) {
            System.out.println(quota);
            quota++;
            armed = quota > 10;
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
