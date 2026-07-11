public class GenCleanWhileTrueBreak001 {
    static int spin(int limit) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > limit) {
                break;
            }
        }
        return rounds;
    }
}
