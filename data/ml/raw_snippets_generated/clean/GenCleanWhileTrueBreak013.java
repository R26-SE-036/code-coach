public class GenCleanWhileTrueBreak013 {
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

    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }
}
