public class GenArrayIndexFix115 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int drain2(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }
}
