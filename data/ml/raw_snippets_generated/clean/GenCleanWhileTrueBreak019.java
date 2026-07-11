public class GenCleanWhileTrueBreak019 {
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
