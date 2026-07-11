public class GenCleanWhileTrueBreak009 {
    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static int spin(int steps) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > steps) {
                break;
            }
        }
        return rounds;
    }
}
