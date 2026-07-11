public class GenCleanWhileTrueBreak002 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describe2(int quota) {
        if (quota < 10) {
            return "low";
        } else if (quota > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe3(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven4(int count) {
        return count % 2 == 0;
    }

    static int spin(int points) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > points) {
                break;
            }
        }
        return rounds;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
