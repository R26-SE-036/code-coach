public class GenCleanWhileTrueBreak004 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int spin(int quota) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > quota) {
                break;
            }
        }
        return rounds;
    }
}
