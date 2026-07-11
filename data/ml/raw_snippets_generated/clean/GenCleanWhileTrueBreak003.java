public class GenCleanWhileTrueBreak003 {
    static int spin(int total) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > total) {
                break;
            }
        }
        return rounds;
    }
}
