public class GenCleanWhileTrueBreak017 {
    static int spin(int attempts) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > attempts) {
                break;
            }
        }
        return rounds;
    }
}
