public class GenWhileNoUpdateFix119 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static void pump(boolean done, int count) {
        while (!done) {
            System.out.println(count);
            count++;
            done = count > 10;
        }
    }
}
